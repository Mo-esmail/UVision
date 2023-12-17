using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace UVISION.Controllers;

[Authorize]
public class DashboardController : Controller
{
    public IActionResult Dashboard()
    {
        return View();
    }
}