package main

import (
	"context"
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/websocket/v2"

	"entgo.io/ent/dialect"

	_ "github.com/mattn/go-sqlite3"

	"github.com/vncz14/incantation/backend/ent"
	"github.com/vncz14/incantation/backend/ent/migrate"

	"github.com/vncz14/incantation/backend/handlers"
)

func main() {
	// Initialize Ent client with SQLite
	client, err := ent.Open(dialect.SQLite, "file:ent.db?_fk=1")
	if err != nil {
		log.Fatalf("failed opening connection to sqlite: %v", err)
	}
	defer client.Close()
	ctx := context.Background()

	err = client.Schema.Create(
		ctx,
		migrate.WithDropIndex(true),
		migrate.WithDropColumn(true),
	)

	if err != nil {
		log.Fatalf("failed creating schema resources: %v", err)
	}

	// Fiber instance
	app := fiber.New()

	app.Use(cors.New(cors.Config{
		AllowOrigins:     "http://localhost:3000",
		AllowCredentials: true,
	}))

	handlers.RegisterAuthRoutes(app.Group("/auth"), client)

	// Routes
	app.Get("/", func(c *fiber.Ctx) error {
		examples, err := client.Example.Query().All(ctx)
		if err != nil {
			return c.Status(500).SendString(err.Error())
		}
		return c.JSON(examples)
	})

	app.Post("/", func(c *fiber.Ctx) error {
		type reqBody struct {
			Name string `json:"name"`
		}
		var body reqBody

		err := c.BodyParser(&body)
		if err != nil {
			return c.Status(400).SendString("Invalid request")
		}

		example, err := client.Example.Create().SetName(body.Name).Save(ctx)
		if err != nil {
			return c.Status(500).SendString(err.Error())
		}
		return c.JSON(example)
	})

	app.Get("/ws", websocket.New(func(c *websocket.Conn) {
		defer c.Close()
		for {
			_, _, err := c.ReadMessage()
			if err != nil {
				break
			}
			if err := c.WriteMessage(websocket.TextMessage, []byte("I just say this back to whatever you say")); err != nil {
				break
			}
		}
	}))

	// Start server
	log.Fatal(app.Listen(":8000"))
}
