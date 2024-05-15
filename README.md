
# Islamic Board Game (IBG) 🕌

## Project Description 📜

Islamic Board Game (IBG) aims to reproduce popular games like Undercover and Codenames with an Islamic twist. The goal is to create an engaging way for people to learn about Islamic words and concepts while playing.

### Game Descriptions

- **Undercover**: Undercover is a social deduction game where players are assigned roles secretly. Some players are undercover agents, while others are regular citizens. The objective of the game is for the undercover agents to blend in and avoid detection, while the citizens try to uncover and identify the undercover agents.

- **Codenames**: Codenames is a word-based party game where players are divided into two teams. Each team has a spymaster who gives one-word clues to help their team guess the words associated with their agents on the board. The challenge is to avoid guessing the words associated with the opposing team and the deadly assassin word.

## Project Structure 📂

The project is organized as follows:

### ibg Folder

- **api** 📑
  - **controllers**: Contains all the logic and queries to the PostgreSQL database.
  - **models**: Includes all FastAPI input and output models as well as the database models.
  - **routers**: Contains the routes for the FastAPI app.

- **socketio** ⚡
  - **controllers**: Contains all the logic and queries to the PostgreSQL and Redis databases.
  - **models**: Includes all Redis OM models.
  - **routers**: Contains all the routes to call the Socket.IO app.

### tests Folder 🧪

- Mirrors the structure of the `ibg` folder.
- Contains tests for routes, models, and controllers within `api` and `socketio`.

## Backend 🖥️

- **FastAPI**: Handles the main API logic.
- **Socket.IO**: Manages real-time communication, mounted on the FastAPI app.
- **SQLModel**: Used as the ORM for database interactions.
- **Redis OM Python**: Interacts with Redis to manage active rooms and games.

### Databases 🗄️

- **PostgreSQL**: Stores users, rooms, games, room events, and game events.
- **Redis**: Stores active rooms and games to handle game logic efficiently.

## Frontend 🌐

- **Next.js**: The frontend framework used for building the user interface.

## Deployment Plan 🚀

### AWS Services ☁️

- **AWS Lambda**: Deploy the FastAPI app (including the mounted Socket.IO app).
- **AWS RDS**: Use for PostgreSQL database.
- **AWS Amplify**: Deploy the frontend.
- **AWS SNS and SES**: Send emails and SMS notifications.

### Infrastructure 🏗️

- **CI/CD**: Plan to use GitHub Actions for continuous integration and deployment.

## Getting Started 🏁

### Prerequisites

- Python 3.10+
- Docker
- Docker Compose

### Installation ⚙️

1. **Clone the repository**:
    ```bash
    git clone git@github.com:Souhib/IBG_API.git
    cd islamic-board-game
    ```

2. **Build and run with Docker Compose**:
    ```bash
    docker-compose up --build
    ```

### Running the Application ▶️

- The application will be available at:
    - FastAPI: `http://localhost:8000`
    - Socket.IO: `http://localhost:8000/socketio`

### Running Tests ✔️

```bash
cd tests
pytest
```

## Contributing 🤝

Contributions are welcome! Please fork the repository and submit a pull request for review.

## License 📄

This project is licensed under the MIT License.

## Contact 📬

For questions or suggestions, please open an issue in the repository.
