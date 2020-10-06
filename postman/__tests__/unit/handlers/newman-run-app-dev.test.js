/* jshint esversion: 8 */
/* jshint node: true */
const newmanRun = require('../../../src/newman_run.js');

describe('Test for app-dev collection', function () {
  it('Verifies the newman run for app-dev', () => {
    // Mock console.log statements so we can verify them. For more information, see
    // https://jestjs.io/docs/en/mock-functions.html
    console.info = jest.fn();

    const newmanResult = newmanRun.handler();

    expect(console.info).toHaveBeenCalledWith("start newman run");
  });
});
