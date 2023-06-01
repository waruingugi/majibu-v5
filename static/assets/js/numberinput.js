{
    const intRx = /\d/,
    integerChange = (event) => {
        if (
        (event.key.length > 1) ||
        event.ctrlKey ||
        ( (event.key === "-") && (!event.currentTarget.value.length) ) ||
        intRx.test(event.key)
        ) return;
        event.preventDefault();
    };

    for (let input of document.querySelectorAll(
    'input[type="number"][step="1"]'
    )) input.addEventListener("keydown", integerChange);

}