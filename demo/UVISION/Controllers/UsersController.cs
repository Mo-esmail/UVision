using System.Collections;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using UVISION.Data;
using UVISION.Models;

namespace UVISION.Controllers;
[Authorize]
public class UsersController : Controller
{
    private ApplicationDbContext _context;

    public UsersController(
        ApplicationDbContext context
    )
    {
        _context = context;
    }

    public IActionResult GetAllUsers()
    {
        List<MyUserViewModel> myUserViewModels = new List<MyUserViewModel>();
        if (myUserViewModels == null)
        {
            throw new ArgumentNullException(nameof(myUserViewModels));
        }

        List<IdentityUser> identityUsers = _context.Users.ToList() ?? throw new ArgumentNullException($"_context.Users.ToList()");
        var response = _context.Users.Select(x => new MyUserViewModel
        {
            userName = x.UserName
        }).ToList();
        return View(response);
    }

}