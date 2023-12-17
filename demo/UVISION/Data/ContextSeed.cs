using Microsoft.AspNetCore.Identity;
using UVISION.Models;

namespace UVISION.Data;

public class ContextSeed
{
    public static async Task SeedRolesAsync(UserManager<IdentityUser> userManager, RoleManager<IdentityRole> roleManager)
    {
        //Seed Roles
        await roleManager.CreateAsync(new IdentityRole(Enums.Roles.SuperAdmin.ToString()));
        await roleManager.CreateAsync(new IdentityRole(Enums.Roles.Admin.ToString()));
        await roleManager.CreateAsync(new IdentityRole(Enums.Roles.Moderator.ToString()));
        await roleManager.CreateAsync(new IdentityRole(Enums.Roles.Basic.ToString()));
    }
}