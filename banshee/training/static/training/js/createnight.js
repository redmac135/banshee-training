function createnight(url) {
    fetch(url, {
        format: "json",
    })
        .then(setTimeout(function() {
            window.location.reload()
        }, 200))
}