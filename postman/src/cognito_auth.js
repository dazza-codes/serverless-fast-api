/* jshint esversion: 8 */
/* jshint node: true */

// The amazon-cognito-identity-js package assumes fetch is available in a web browser.  Since
// nodejs does not have fetch built-in it is emulated like this:
global.fetch = require("node-fetch");
const AmazonCognitoIdentity = require("amazon-cognito-identity-js");

function asyncCognitoAuthentication(cognitoConfig) {
  const cognitoUserPool = new AmazonCognitoIdentity.CognitoUserPool({
    UserPoolId: cognitoConfig.userPoolId,
    ClientId: cognitoConfig.clientId,
  });
  const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
    Username: cognitoConfig.username,
    Pool: cognitoUserPool,
  });
  const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(
    {
      Username: cognitoConfig.username,
      Password: cognitoConfig.password,
    }
  );

  return new Promise(function (resolve, reject) {
    cognitoUser.authenticateUser(authenticationDetails, {
      onSuccess: resolve,
      onFailure: reject,
      newPasswordRequired: resolve,
    });
  });
}

const cognitoJWT = {
  session: undefined,
  jwtAccess: undefined,
  jwtId: undefined,
  jwtRefresh: undefined,
  jwtPayloads: undefined,
};

module.exports.getCognitoJWT = async function (cognitoConfig) {
  try {
    const session = await asyncCognitoAuthentication(cognitoConfig);
    cognitoJWT.session = session;
    cognitoJWT.jwtAccess = session.getAccessToken().getJwtToken();
    cognitoJWT.jwtId = session.getIdToken().getJwtToken();
    cognitoJWT.jwtRefresh = session.getRefreshToken().getToken();
    cognitoJWT.jwtPayloads = {
      jwtAccess: session.getAccessToken().decodePayload(),
      jwtId: session.getIdToken().decodePayload(),
    };
    return cognitoJWT;
  } catch (error) {
    console.log(error.message);
  }
};

const process = require("process");
if (process.env.TEST_AUTH === "test") {
  const config = require("config");
  const cognitoConfig = config.get("cognito");
  console.log(cognitoConfig);

  Promise.resolve(module.exports.getCognitoJWT(cognitoConfig)).then(
    (cognitoJWT) => {
      console.log(cognitoJWT);
    }
  );
}
