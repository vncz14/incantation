package main

import (
	"context"
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/websocket/v2"

	"entgo.io/ent/dialect"

	_ "github.com/mattn/go-sqlite3"

	"github.com/vncz14/incantation/backend/ent"
)

func main() {
	// Initialize Ent client with SQLite
	client, err := ent.Open(dialect.SQLite, "file:ent.db?_fk=1")
	if err != nil {
		log.Fatalf("failed opening connection to sqlite: %v", err)
	}
	defer client.Close()
	ctx := context.Background()
	if err := client.Schema.Create(ctx); err != nil {
		log.Fatalf("failed creating schema resources: %v", err)
	}

	// Fiber instance
	app := fiber.New()

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
