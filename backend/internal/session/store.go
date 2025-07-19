package session

import (
	"os"
	"time"

	"github.com/gofiber/fiber/v2/middleware/session"
)

var Store = session.New(session.Config{
	Expiration:     8 * time.Hour,
	CookieSecure:   os.Getenv("INCANTATION_DEBUG") != "true",
	CookieHTTPOnly: true,
	CookieSameSite: "Lax",
})
