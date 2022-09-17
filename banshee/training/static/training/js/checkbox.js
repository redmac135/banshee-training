// Check already checked boxes
window.addEventListener("load", (event) => {
    initialcheck()
})

function initialcheck() {
    $(".slot_checkbox_table input[type=checkbox]:checked").each(function() {
        var label = $("label[for='" + $(this).attr('id') + "']");
        animate_check(label);
    })
}

function checkChild(element) {
    let child = $(element).children("input")[0];
    let label = $(element).find("label");
    child.checked = !child.checked;
    if (child.checked) {
        animate_check(label)
    } else {
		animate_uncheck(label)
	}
}

function animate_uncheck(label) {
    label.addClass("shadow-md");
    label.removeClass("m-3");
    label.removeClass("p-3");
    label.removeClass("bg-yellow-500");
}

function animate_check(label) {
    label.removeClass("shadow-md");
    label.addClass("m-3");
    label.addClass("p-3");
    label.addClass("bg-yellow-500");
}