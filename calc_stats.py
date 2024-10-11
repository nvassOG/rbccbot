import discord
import json
import asyncio

TOKEN = 'TOKEN_HERE'

# Use the appropriate intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

client = discord.Client(intents=intents)

# Load game logs from JSON file
def load_game_logs():
    with open('game_logs.json', 'r') as f:
        return json.load(f)

# Load player data from JSON file
def load_player_data():
    with open('player_ids.json', 'r') as f:
        return json.load(f)

# Load character data from JSON file
def load_characters():
    with open('characters.json', 'r') as f:
        return json.load(f)

# Calculate stats for a specific player with optional character analysis
def calculate_stats(player_id, character_name=None):
    game_logs = load_game_logs()
    characters = load_characters()

    # Initialize variables for overall stats
    total_games = len(game_logs)
    good_wins = sum(1 for game in game_logs if game['winner'] == "Good")
    evil_wins = total_games - good_wins

    # Initialize variables for player-specific stats
    total_player_games = 0
    player_good_games = 0
    player_evil_games = 0
    player_good_wins = 0
    player_evil_wins = 0

    # Initialize variables for character-specific stats
    character_games = 0
    character_wins = 0

    # Loop through each game and update player-specific stats
    for game in game_logs:
        # Check if the player participated in this game
        player_in_game = next((player for player in game['players'] if player['id'] == player_id), None)
        if player_in_game:
            total_player_games += 1  # Count total games played by the player

            # Check if the player is on the Good team
            if player_in_game['alignment'] == "Good":
                player_good_games += 1  # Increment total Good games played
                if game['winner'] == "Good":
                    player_good_wins += 1  # Increment Good wins if the team won

            # Check if the player is on the Evil team
            elif player_in_game['alignment'] == "Evil":
                player_evil_games += 1  # Increment total Evil games played
                if game['winner'] == "Evil":
                    player_evil_wins += 1  # Increment Evil wins if the team won

            # Check if the player played as the specified character
            if character_name and player_in_game.get('role') == character_name:
                character_games += 1
                if (game['winner'] == "Good" and player_in_game['alignment'] == "Good") or \
                   (game['winner'] == "Evil" and player_in_game['alignment'] == "Evil"):
                    character_wins += 1

    # Calculate win percentages
    player_good_win_percentage = (player_good_wins / player_good_games * 100) if player_good_games > 0 else 0
    player_evil_win_percentage = (player_evil_wins / player_evil_games * 100) if player_evil_games > 0 else 0

    # Calculate character win percentage
    character_win_percentage = (character_wins / character_games * 100) if character_games > 0 else 0

    stats = {
        'total_games': total_games,
        'total_good_wins': good_wins,
        'total_evil_wins': evil_wins,
        'total_player_games': total_player_games,
        'player_good_games': player_good_games,
        'player_evil_games': player_evil_games,
        'player_good_wins': player_good_wins,
        'player_evil_wins': player_evil_wins,
        'player_good_win_percentage': player_good_win_percentage,
        'player_evil_win_percentage': player_evil_win_percentage,
        'character_games': character_games,
        'character_wins': character_wins,
        'character_win_percentage': character_win_percentage,
    }

    return stats

# Calculate top 5 characters by win rate for a specific player
def calculate_top_characters(player_id):
    game_logs = load_game_logs()
    character_stats = {}

    # Loop through each game to gather character stats
    for game in game_logs:
        # Check if the player participated in this game
        player_in_game = next((player for player in game['players'] if player['id'] == player_id), None)
        if player_in_game:
            character_name = player_in_game.get('role')
            if character_name:
                # Initialize character stats if not present
                if character_name not in character_stats:
                    character_stats[character_name] = {'games': 0, 'wins': 0}
                character_stats[character_name]['games'] += 1

                # Check if the player's team won
                if (game['winner'] == "Good" and player_in_game['alignment'] == "Good") or \
                   (game['winner'] == "Evil" and player_in_game['alignment'] == "Evil"):
                    character_stats[character_name]['wins'] += 1

    # Calculate win rates for each character and sort by win rate
    character_win_rates = [
        {'character': char, 'win_rate': (stats['wins'] / stats['games'] * 100) if stats['games'] > 0 else 0}
        for char, stats in character_stats.items()
    ]
    character_win_rates.sort(key=lambda x: x['win_rate'], reverse=True)

    # Get the top 5 characters by win rate
    top_5_characters = character_win_rates[:5]
    return top_5_characters

# Send a Discord message with the calculated stats in the same channel
async def send_discord_message(channel, stats, player_name, character_name=None):
    discord_message = (
        f"**Stats for {player_name}**\n"
        f"Total games played: {stats['total_player_games']}\n"
        f"Total Good games played: {stats['player_good_games']}\n"
        f"Total Evil games played: {stats['player_evil_games']}\n"
        f"Total Good wins: {stats['player_good_wins']}\n"
        f"Total Evil wins: {stats['player_evil_wins']}\n"
        f"Good win percentage: {stats['player_good_win_percentage']:.2f}%\n"
        f"Evil win percentage: {stats['player_evil_win_percentage']:.2f}%\n"
    )

    if character_name:
        discord_message = (
            f"\n**Stats for {player_name} being {character_name}**\n"
            f"Total games played as {character_name}: {stats.get('character_games', 0)}\n"
            f"Total wins as {character_name}: {stats.get('character_wins', 0)}\n"
            f"Win percentage as {character_name}: {stats.get('character_win_percentage', 0):.2f}%\n"
        )

    await channel.send(discord_message)

# Send a Discord message with the top 5 characters by win rate
async def send_top_characters_message(channel, top_characters, player_name):
    discord_message = f"**Top 5 Characters by Win Rate for {player_name}**\n"
    for char in top_characters:
        discord_message += f"{char['character']}: {char['win_rate']:.2f}%\n"
    
    await channel.send(discord_message)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return

    # Check if the message starts with '!stats'
    if message.content.startswith('!stats'):
        parts = message.content.split()
        if len(parts) >= 2:
            player_id = parts[1]
            player_data = load_player_data()
            player_name = player_data.get(player_id, "Unknown")

            if player_name != "Unknown":
                # Check if the user wants character-specific stats or top characters
                if len(parts) == 3 and parts[2].lower() == 'characters':
                    top_characters = calculate_top_characters(player_id)
                    await send_top_characters_message(message.channel, top_characters, player_name)
                else:
                    character_name = parts[2] if len(parts) > 2 else None

                    # Validate character name
                    valid_characters = [char['name'] for char in load_characters()]
                    if character_name and character_name not in valid_characters:
                        await message.channel.send(f"{character_name} is not a valid character.")
                        return

                    stats = calculate_stats(player_id, character_name)
                    await send_discord_message(message.channel, stats, player_name, character_name)
            else:
                await message.channel.send(f"Player ID {player_id} not found.")

# Run the bot
client.run(TOKEN)
