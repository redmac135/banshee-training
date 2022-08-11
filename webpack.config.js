const path = require('path');

module.exports = {
    mode: "development",
    entry: {
        navbar: './banshee/assets/base/js/navbar.js'
    },  // path to input file
    output: {
        filename: '[name]/js/[name]-bundle.js',  // output bundle file name
        path: path.resolve(__dirname, './banshee/static'),  // path to Django static directory
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                loader: "babel-loader",
                options: {
                    presets: [
                        "@babel/preset-env",
                    ]
                }
            },
        ],
    },
};