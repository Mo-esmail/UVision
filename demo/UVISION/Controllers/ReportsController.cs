using Amazon.DynamoDBv2.DataModel;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using NuGet.Packaging.Signing;
using UVISION.Models;

namespace UVISION.Controllers;
[Authorize]
public class ReportsController : Controller
{
    private readonly IDynamoDBContext _dynamoDBContext;
    
    public ReportsController(IDynamoDBContext dynamoDBContext)
    {
        _dynamoDBContext = dynamoDBContext;
    }
    
    public async Task<IActionResult> AllReports(string DeviceID = "D7")
    {
        var product = await _dynamoDBContext.QueryAsync<Report>(DeviceID).GetRemainingAsync();
        return View(product);
    }
    
}