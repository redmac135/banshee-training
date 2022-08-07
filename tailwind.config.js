module.exports = {
    content: [
        "./banshee/templates/*.html",
        "./banshee/templates/**/*.html",
        "./banshee/**/templates/**/*.html",
    ],
    theme: {
        extend: {
            colors: {
                "clr-1": "#052324",
                "clr-2": "#314448",
                "clr-3": "#1DCA7F",
                "clr-4": "#7EE8B9",
                "clr-5": "#DBF4EA"
            }
        }
    }
};
