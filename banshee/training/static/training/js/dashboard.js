function createnight(url) {
    fetch(url, {
        format: "json",
    })
        .then(setTimeout(function() {
            window.location.reload()
        }, 200))
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        let cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = jQuery.trim(cookie);
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }
    return cookieValue;
}

function deletenight(url) {
    fetch(url, {
        method: "delete",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
    })
        .then(setTimeout(function() {
            window.location.reload()
        }, 200))
}

