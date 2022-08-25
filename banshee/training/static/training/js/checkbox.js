function checkChild(element) {
    let child = $(element).children("input")[0];
    let label = $(element).find("label");
    console.log(typeof(label))
    child.checked = !child.checked;
    if (child.checked) {
        label.removeClass("shadow-md");
        label.addClass("m-3");
        label.addClass("p-3");
        label.addClass("bg-yellow-500");
    } else {
		label.addClass("shadow-md");
		label.removeClass("m-3");
        label.removeClass("p-3");
		label.removeClass("bg-yellow-500");
	}
}