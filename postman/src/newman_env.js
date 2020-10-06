/* jshint esversion: 8 */
/* jshint node: true */

const config = require("config");
const cognito_auth = require("./cognito_auth.js");
const { v4: uuidv4 } = require("uuid");

module.exports.getNewmanEnv = async function () {
  const BASE_URL = config.get("baseURL");

  const cognitoConfig = config.get("cognito");
  // console.log(cognitoConfig);

  try {
    const cognitoJWT = await cognito_auth.getCognitoJWT(cognitoConfig);
    const newman_env = {
      id: uuidv4(),
      name: "newman_env",
      values: [
        {
          key: "BaseURL",
          value: BASE_URL,
          enabled: true,
        },
        {
          key: "COGNITO_JWT",
          value: cognitoJWT.jwtAccess,
          enabled: true,
        }
      ],
      _postman_variable_scope: "environment",
      _postman_exported_at: new Date(Date.now()).toISOString(),
      _postman_exported_using: "Postman/7.26.0",
    };
    return newman_env;
  } catch (error) {
    console.log(error.message);
  }
};

const process = require("process");
if (process.env.TEST_ENV === "test") {
  Promise.resolve(module.exports.getNewmanEnv()).then((result) => {
    console.log(result);
  });
}
