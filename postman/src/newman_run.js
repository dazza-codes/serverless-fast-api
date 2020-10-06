/* jshint esversion: 8 */
/* jshint node: true */

// https://github.com/postmanlabs/newman#api-reference

// When this module runs in a lambda function, all the log
// statements are written to CloudWatch by default. For more information, see
// https://docs.aws.amazon.com/lambda/latest/dg/nodejs-prog-model-logging.html

"use strict";

const process = require("process");
console.log("CONFIG_FILE: ", process.env.CONFIG_FILE);
console.log("NODE_ENV: ", process.env.NODE_ENV);

const config = require("config");
const newman = require("newman");
const newmanEnv = require("./newman_env.js");
const { v4: uuidv4 } = require("uuid");
const winston = require("winston");

const logLevel = config.get("logLevel", "info");

// const winstonOptions = {
//   format: winston.format.combine(
//     winston.format.timestamp(),
//     winston.format.json()
//   ),
//   level: logLevel,
//   defaultMeta: { service: "newman" },
//   transports: [new winston.transports.Console()],
// };

const winstonOptions = {
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.simple()
  ),
  level: logLevel,
  defaultMeta: { service: "newman" },
  transports: [new winston.transports.Console()],
};
const logger = winston.createLogger(winstonOptions);


const getNewmanEnvironment = async function () {
  try {
    const env = await newmanEnv.getNewmanEnv();
    return env;
  } catch (error) {
    logger.error(error);
  }
};


/**
 * A Lambda function that runs a postman collection
 */
module.exports.runNewmanTest = async () => {
  const newmanEnv = await getNewmanEnvironment();
  logger.info("environment: ", newmanEnv);

  const postmanCollection = config.get("postmanCollection");
  logger.info("collection: ", postmanCollection);

  const newmanOptions = {
    collection: require(postmanCollection),
    environment: newmanEnv,
    color: "off",
    reporters: "cli",
    // reporters: ["cli", "winston"],
    // reporter: { winston: winstonOptions },
  };

  logger.info("start newman run");
  newman
    .run(newmanOptions)
    .on("start", function (err, args) {
      logger.info("running a collection...");
    })
    .on("done", function (err, summary) {
      if (err || summary.error) {
        logger.error("error: ", err);
        return {
          statusCode: 500,
          body: summary,
        };
      } else {
        logger.info("collection run completed.");
        logger.info({ summary: summary });
        return {
          statusCode: 200,
          body: summary,
        };
      }
    });

};

module.exports.handler = event => {
  // event is ignored, all input params are in process.env and config file
  Promise.resolve(module.exports.runNewmanTest()).then((result) => {
    console.log(result);
    return result;
  });
};

if (process.env.NEWMAN_RUN === "true") {
  module.exports.handler();
}
