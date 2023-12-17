using Amazon.DynamoDBv2.DataModel;
using NuGet.Packaging.Signing;

namespace UVISION.Models;

[DynamoDBTable("DataLogs")]
public class Report
{
    [DynamoDBHashKey("DeviceID")]
    public string DeviceID { get; set; }

    [DynamoDBRangeKey("Timestamp")]
    public long Timestamp { get; set; }

    [DynamoDBProperty("location")]
    public string location { get; set; }
    
    [DynamoDBProperty("No_Of_Cars")]
    public string No_Of_Cars { get; set; }
    
    
    
}