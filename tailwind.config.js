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
                "clr-5": "#DBF4EA",
                "banshee-green": {
                    50: "#82EDBF",
                    100: "#70EBB6",
                    200: "#add1eb",
                    300: "#4CE6A3",
                    400: "#3BE39A",
                    500: "#29EO91",
                    600: "#1DCA7F", // Default Clr-3
                    700: "#1CC47B",
                    800: "#19B370",
                    900: "#17A165",
                }
            }
        }
    }
};
