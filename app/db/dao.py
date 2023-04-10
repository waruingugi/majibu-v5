from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    Protocol,
    TypedDict,
    Sequence,
    cast,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session, Load
from sqlalchemy import insert, inspect, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils import get_hybrid_properties

from datetime import datetime

from app.db.base_class import Base, generate_uuid
from app.exceptions.custom import HttpErrorException, ObjectDoesNotExist
from app.errors.custom import ErrorCodes
from http import HTTPStatus
from app.core.raw_logger import logger
from fastapi_sqlalchemy_filter import Filter
from sqlalchemy.orm.strategy_options import _AbstractLoad
from app.db.filters import _create_filtered_query
from fastapi_pagination.ext.sqlalchemy import paginate_query
from fastapi_pagination import Params
from sqlalchemy.sql import Select
from sqlalchemy.engine import Row


# Custom Types
ModelType = TypeVar("ModelType", bound=Base)
CreateSerializer = TypeVar("CreateSerializer", bound=BaseModel)
UpdateSerializer = TypeVar("UpdateSerializer", bound=BaseModel)
LoadOption = Union[_AbstractLoad, Load]


# Class that we can use to keep track of the changes in an object
class ChangeAttrState(TypedDict):
    before: Any
    after: Any


ChangedObjState = Dict[str, ChangeAttrState]


class DaoInterface(Protocol[ModelType]):
    """
    Parent class uses ´Protocol´ which ensures child classes inherit
    the same functions or structure.
    """

    model: ModelType

    def on_relationship(
        self,
        db: Session,
        *,
        id: str,
        values: dict,
        db_obj: Optional[ModelType] = None,
        create: bool = True,
    ) -> None:
        pass

    def get_not_none(self, db: Session, **filters: Any) -> ModelType:
        pass

    def create(self, db: Session, *, obj_in: CreateSerializer) -> ModelType:
        pass

    def get(self, db: Session, **filters: Any) -> Optional[ModelType]:
        pass

    def get_or_none(self, db: Session, **filters: Any) -> ModelType:
        pass

    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        pass

    def on_post_create(
        self, db: Session, db_obj: Union[ModelType, List[ModelType]]
    ) -> None:
        pass

    def on_pre_update(
        self, db: Session, db_obj: ModelType, values: dict, orig_values: dict
    ) -> None:
        pass

    def on_post_update(
        self, db: Session, db_obj: ModelType, changed: ChangedObjState
    ) -> None:
        pass


class CreateDao(Generic[ModelType, CreateSerializer]):
    def __init__(self, model: Type[ModelType]):
        # super(CreateDao, self).__init__(model)
        self.model = model

    def create(
        self: Union[Any, DaoInterface], db: Session, obj_in: CreateSerializer
    ) -> ModelType:
        obj_in_data = obj_in.dict(exclude_none=True)
        orig_data = obj_in_data.copy()

        relationship_fields = inspect(self.model).relationships.keys()

        for key in list(obj_in_data.keys()):
            if (
                isinstance(obj_in_data[key], list)
                or key in relationship_fields
                or key not in self.model.get_model_columns()
                or obj_in_data[key] is None
            ):
                del obj_in_data[key]

        try:
            obj_id = obj_in_data.pop("id", None) or generate_uuid()
            if hasattr(self, "on_pre_create"):
                self.on_pre_create(
                    db, id=obj_id, values=obj_in_data, orig_values=orig_data
                )

            stmt = insert(self.model.__table__).values(id=obj_id, **obj_in_data)
            db.execute(stmt)

            if hasattr(self, "on_relationship"):
                self.on_relationship(db, id=obj_id, values=orig_data)

            db.commit()
            db_obj = self.get(db, id=obj_id)
            self.on_post_create(db, db_obj)

            return db_obj
        except IntegrityError as integrity_error:
            logger.warning(integrity_error)
            db.rollback()

    def on_pre_create(
        self, db: Session, id: str, values: dict, orig_values: dict
    ) -> None:
        pass

    def on_post_create(
        self, db: Session, db_obj: Union[ModelType, List[ModelType]]
    ) -> None:
        pass


class UpdateDao(Generic[ModelType, UpdateSerializer]):
    def __init__(self, model: Type[ModelType]):
        self.model = model
        # super(UpdateDao, self).__init__()

    def update(
        self: Union[Any, DaoInterface],
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSerializer, Dict[str, Any]],
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in

        else:
            update_data = obj_in.dict(exclude_unset=True)

        if not update_data:
            raise HttpErrorException(
                status_code=HTTPStatus.BAD_REQUEST,
                error_code=ErrorCodes.NO_CHANGES_DETECTED.name,
                error_message=ErrorCodes.NO_CHANGES_DETECTED.value,
            )

        if "created_at" in update_data:
            del update_data["created_at"]

        if not hasattr(db_obj, "updated_at"):
            update_data["update_at"] = datetime.now()

        hybrid_property_fields = get_hybrid_properties(self.model).keys()
        relationship_fields = inspect(self.model).relationships.keys()

        orig_update_data = update_data.copy()

        for key in list(update_data.keys()):
            if (
                key in hybrid_property_fields
                or key in relationship_fields
                or key not in db_obj.get_model_columns()
                or update_data[key] is None
            ):
                del update_data[key]

        self.on_pre_update(
            db=db, db_obj=db_obj, values=update_data, orig_values=orig_update_data
        )

        # We need to keep track of attributes we are about to change
        changed_obj_state: ChangedObjState = {}
        for key in list(update_data.keys()):
            if key == "updated_at":
                continue

            if key in db_obj.get_model_columns():
                # Field has the same values, so we delete it
                if update_data[key] == getattr(db_obj, key):
                    del update_data[key]

                # Field has changed, so we track it
                else:
                    changed_obj_state[key] = {
                        "before": getattr(db_obj, key),
                        "after": update_data[key],
                    }

        stmt = (
            update(self.model.__table__)
            .where(self.model.id == db_obj.id)
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        db.execute(stmt)

        if hasattr(self, "on_relationship"):
            self.on_relationship(
                db, id=db_obj.id, values=orig_update_data, db_obj=db_obj, create=False
            )

        try:
            db.commit()

            updated_db_obj = self.get_not_none(db, id=db_obj.id)
            self.on_post_update(db, updated_db_obj, changed_obj_state)

            return updated_db_obj
        except IntegrityError as integrity_error:
            db.rollback()
            logger.warning(integrity_error)
            raise

    def on_pre_update(
        self, db: Session, db_obj: ModelType, values: dict, orig_values: dict
    ) -> None:
        pass

    def on_post_update(
        self, db: Session, db_obj: ModelType, changed: ChangedObjState
    ) -> None:
        pass


class DeleteDao(Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
    ):
        # super(DeleteDao, self).__init__()
        self.model = model

    def on_post_delete(self, db: Session, db_obj: ModelType) -> None:
        pass

    def remove(self, db: Session, *, id: str) -> Optional[ModelType]:
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
            self.on_post_delete(db, obj)
            return obj

        return None


class ReadDao(Generic[ModelType]):
    def __init__(
        self,
        model: Type[ModelType],
    ):
        self.model = model

    def get_not_none(
        self,
        db: Session,
        load_options: Optional[Sequence[LoadOption]] = None,
        **filters,
    ) -> ModelType:
        obj = self.get(db, load_options, **filters)
        if not obj:
            raise ObjectDoesNotExist
        return obj

    def get_all(
        self,
        db: Session,
        load_options: Optional[Sequence[LoadOption]] = None,
        **filters,
    ) -> List[ModelType]:
        query = db.query(self.model)

        query = _create_filtered_query(query, filters)
        if load_options:
            query = query.options(*load_options)

        return query.all()  # type: ignore

    def get_by_ids(self, db: Session, *, ids: List[str]) -> List[ModelType]:
        return db.query(self.model).filter(self.model.id.in_(ids)).all()

    def get(
        self: Union[Any, DaoInterface],
        db: Session,
        load_options: Optional[Sequence[LoadOption]] = None,
        **filters,
    ) -> Optional[ModelType]:
        query = db.query(self.model)
        query = _create_filtered_query(query, filters)

        if load_options:
            query = query.options(*load_options)
        return query.filter_by(**filters).first()  # type: ignore

    def search(
        self: Union[Any, DaoInterface],
        db: Session,
        search_filter: Filter | Dict,
    ) -> Sequence[Row]:
        query = db.query(self.model)
        query = _create_filtered_query(query, search_filter)

        return db.scalars(query).all()

    def get_multi_paginated(
        self: Union[Any, DaoInterface],
        db: Session,
        search_filter: Filter | Dict,
        params: Params,
    ) -> Sequence[Row]:
        query = db.query(self.model)
        query = _create_filtered_query(query, search_filter)
        query = cast(Select, query)
        query = paginate_query(query, params)

        return db.scalars(query).all()


class CRUDDao(
    CreateDao[ModelType, CreateSerializer],
    UpdateDao[ModelType, UpdateSerializer],
    DeleteDao[ModelType],
    ReadDao[ModelType],
):
    def __init__(self, model: Type[ModelType]):
        super().__init__(model)
