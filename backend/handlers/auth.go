package handlers

import (
	"context"
	"encoding/json"
	"os"

	"github.com/gofiber/fiber/v2"
	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"

	"github.com/vncz14/incantation/backend/ent"
	"github.com/vncz14/incantation/backend/ent/user"

	"github.com/vncz14/incantation/backend/internal/session"
)

var oauthConfig = &oauth2.Config{
	ClientID:     os.Getenv("GOOGLE_CLIENT_ID"),
	ClientSecret: os.Getenv("GOOGLE_CLIENT_SECRET"),
	RedirectURL:  "http://localhost:8000/auth/google/callback", // your backend's callback
	Scopes: []string{
		"openid",
	},
	Endpoint: google.Endpoint,
}

type GoogleUserResp struct {
	Sub string `json:"sub"`
}

func RegisterAuthRoutes(router fiber.Router, client *ent.Client) {
	router.Get("/google/login", func(c *fiber.Ctx) error {
		url := oauthConfig.AuthCodeURL("random_state", oauth2.AccessTypeOffline)
		return c.Redirect(url)
	})

	router.Get("/google/callback", func(c *fiber.Ctx) error {
		code := c.Query("code")
		if code == "" {
			return c.Status(fiber.StatusBadRequest).SendString("Missing code")
		}

		token, err := oauthConfig.Exchange(context.Background(), code)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Token exchange failed")
		}

		client := oauthConfig.Client(context.Background(), token)
		resp, err := client.Get("https://www.googleapis.com/oauth2/v3/userinfo")
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to get user info")
		}
		defer resp.Body.Close()

		var user GoogleUserResp

		err = json.NewDecoder(resp.Body).Decode(&user)

		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to parse user info")
		}

		sess, err := session.Store.Get(c)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to create session")
		}
		sess.Set("sub", user.Sub)
		if err := sess.Save(); err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to save session")
		}

		return c.Redirect("http://localhost:3000/")
	})

	router.Get("/me", func(c *fiber.Ctx) error {
		sess, err := session.Store.Get(c)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to get session")
		}

		sub := sess.Get("sub")
		if sub == nil {
			return c.Status(fiber.StatusUnauthorized).SendString("No user session")
		}

		user, err := client.User.
			Query().
			Where(user.SubEQ(sub.(string))).
			Only(c.Context())

		if err != nil {
			if ent.IsNotFound(err) {
				newUser, err := client.User.
					Create().
					SetSub(sub.(string)).
					Save(c.Context())
				if err != nil {
					return c.Status(fiber.StatusInternalServerError).SendString("Failed to create user: " + err.Error())
				}
				return c.JSON(newUser)
			}
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to query user")
		}

		return c.JSON(user)
	})

	router.Post("/logout", func(c *fiber.Ctx) error {
		sess, err := session.Store.Get(c)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to get session")
		}
		if err := sess.Destroy(); err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString("Failed to destroy session")
		}
		return c.SendStatus(fiber.StatusOK)
	})
}
