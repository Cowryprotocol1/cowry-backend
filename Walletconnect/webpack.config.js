const path = require("path")
const HTMLWebpackPlugin = require('html-webpack-plugin') //plugin handles html rendering to the dist folder

module.exports = {
  mode: "development",
  entry: {
    bundle: path.resolve(__dirname, "src/index.js"),
  },
  output: {
    path: path.resolve(__dirname, "dist"),
    filename: "[name][contenthash].js",
    clean: true,
    assetModuleFilename: "[name][ext]",
  },
  devtool: "source-map",
  devServer: {
    static: {
      directory: path.resolve(__dirname, "dist"),
    },

    port: 3000,
    open: true,
    hot: true,
    compress: true,
    historyApiFallback: true,
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader", // make app backward compatible
          options: {
            presets: ["@babel/preset-env"],
          },
        },
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i, //loader for loading images and gif using webpack,
        type: "asset/resource", // dont forget to use assetModuleFilename in output
      },
    ],
  }, //used mainly for loaders to load files like css, scss
  plugins: [
    new HTMLWebpackPlugin({
      title: "Decentralized Stablecoin",
      filename: "index.html",
      template: "src/template.html", //main template where we right our html
    }),
  ],
};