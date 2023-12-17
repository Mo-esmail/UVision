const AWS = require('aws-sdk');
const ddb = new AWS.DynamoDB.DocumentClient({ apiVersion: '2012-08-10', region: process.env.AWS_REGION });
const { TABLE_NAME } = process.env;
exports.handler = async event => {
  console.log("Event " + JSON.stringify(event));
  let connectionData;
  
  try {
    connectionData = await ddb.scan({ TableName: TABLE_NAME, ProjectionExpression: 'ConnectionID' }).promise();
    console.log("Found connection data " + JSON.stringify(connectionData));
  } catch (e) {
    return { statusCode: 500, body: e.stack };
  }
  
  const apigwManagementApi = new AWS.ApiGatewayManagementApi({
    apiVersion: '2018-11-29',
    endpoint: 'https://sgbnt474rf.execute-api.eu-west-2.amazonaws.com/production'
  });
  
  const IoTData = JSON.stringify(event);

  
  const postCalls = connectionData.Items.map(async ({ ConnectionID }) => {
    let connectionId = ConnectionID;
    console.log("connectionId " + connectionId);
    try {
      await apigwManagementApi.postToConnection({ ConnectionId: connectionId, Data: IoTData }).promise();
    } catch (e) {
      if (e.statusCode === 410) {
        console.log(`Found stale connection, deleting ${connectionId}`);
        await ddb.delete({ TableName: TABLE_NAME, Key: { connectionId } }).promise();
      } else {
        throw e;
      }
    }
  });
  
  try {
    await Promise.all(postCalls);
  } catch (e) {
    return { statusCode: 500, body: e.stack };
  }
  return { statusCode: 200, body: 'Data sent.' };
};
