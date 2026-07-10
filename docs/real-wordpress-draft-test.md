# Real WordPress Draft Test Setup

This checklist is for creating the first real WordPress draft from DAMA.

DAMA still does not publish posts directly.

It only creates WordPress posts with:

    status = draft

## 1. Create WordPress Application Password

In WordPress admin:

1. Go to Users.
2. Open the user profile that DAMA should use.
3. Find Application Passwords.
4. Add a new application password named:

       DAMA Local Draft Connector

5. Copy the generated password once.

Do not paste this password into ChatGPT.

## 2. Create backend/.env.local

Copy:

    backend/.env.local.example

to:

    backend/.env.local

Fill:

    DAMA_WORDPRESS_BASE_URL=https://your-wordpress-site.com
    DAMA_WORDPRESS_USERNAME=your-wordpress-username
    DAMA_WORDPRESS_APP_PASSWORD=your-application-password

## 3. Restart backend

After changing backend/.env.local, restart the backend server.

## 4. Test WordPress status page

Open:

    http://localhost:3000/publishing/wordpress

Run:

1. Dry-run test
2. Real WordPress test

The real test should authenticate with:

    /wp-json/wp/v2/users/me

## 5. Create one real draft

Use a WordPress variant that is:

    ready_for_publish

Then create a WordPress draft with mode:

    wordpress

Check:

    /publishing/attempts

Then open the attempt detail page.

## 6. Safety rules

- Do not commit backend/.env.local.
- Do not use your main admin account if a dedicated editor user can be used.
- Do not enable direct publish yet.
- Do not enable SEO meta sending unless the target site supports it.
