import json
import os
import asyncio
import discord
from discord import Intents

DISCORD_TOKEN = 'TOKEN_HERE'
CHANNEL_ID = 1294006533168037969

def load_player_ids(file_path):
    # Load existing player IDs from the JSON file
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}  # Return an empty dict if the file doesn't exist

def load_characters(file_path):
    # Load character data from the JSON file
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []  # Return an empty list if the file doesn't exist

def parse_game_data(file_path, player_ids, characters):
    # Read the game data from the input file
    with open(file_path, 'r') as f:
        game_data = json.load(f)

    # Initialize the output structure
    parsed_data = {
        'players': [],
        'winner': ''
    }

    # Get player data and their roles
    players = game_data['history'][-1]['data']['players']  # Get final player data
    roles = game_data['history'][-1]['data']['roles']      # Get roles
    role_index = 0  # To track the index of roles

    # Create a dictionary for character data for easy lookup
    character_dict = {char['name']: char for char in characters}

    for player in players:
        player_info = {
            'id': player['id'],  # Player ID
            'name': player_ids.get(player['id'], 'Unknown'),  # Get player name or 'Unknown'
            'role': roles[role_index] if role_index < len(roles) else None  # Assign roles to players
        }
        
        # Check if the role exists in the character dictionary
        if player_info['role'] in character_dict:
            character = character_dict[player_info['role']]
            player_info['type'] = character['type']  # Add character type
            player_info['alignment'] = character['alignment']  # Add character alignment
        else:
            player_info['type'] = None  # If role not found, set type to None
            player_info['alignment'] = None  # If role not found, set alignment to None
        
        # Add only valid players (non-null ID) to the list
        if player['id'] is not None:
            parsed_data['players'].append(player_info)
            role_index += 1  # Increment role index only for valid players

    # Determine the winner
    parsed_data['winner'] = 'Good' if not game_data['history'][-1]['data']['isEvilWin'] else 'Evil'

    return parsed_data

def get_next_id(output_file):
    # Get the next ID by reading the existing game log and counting entries
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            data = json.load(f)
            return len(data) + 1  # Count existing entries and increment by 1
    return 1  # Start with ID 1 if the file doesn't exist

def save_to_json(data, output_file):
    # Save the parsed data to a JSON file
    next_id = get_next_id(output_file)
    data['game_id'] = next_id  # Add incremental ID to the parsed data

    # Load existing data if the file exists
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []  # Start with an empty list if the file doesn't exist

    existing_data.append(data)  # Append new game data to existing data

    # Write the updated data back to the file
    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=4)  # Use indent for pretty printing

def toggle_alignment(players):
    while True:
        change_alignment = input("Has anyone's alignment changed? (y/n): ").strip().lower()
        if change_alignment == 'n':
            break  # Exit if no changes
        elif change_alignment == 'y':
            # Display player options
            print("Select a player to toggle their alignment:")
            for idx, player in enumerate(players):
                print(f"{idx + 1}: {player['name']} (Current Alignment: {player['alignment']})")

            # Get user input for player selection
            try:
                choice = int(input("Enter the player number to toggle their alignment: ")) - 1
                if 0 <= choice < len(players):
                    # Toggle alignment
                    if players[choice]['alignment'] == 'Good':
                        players[choice]['alignment'] = 'Evil'
                    else:
                        players[choice]['alignment'] = 'Good'
                    print(f"Alignment for {players[choice]['name']} changed to {players[choice]['alignment']}.")
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

async def send_discord_message(channel_id, message):
    # Create a Discord client with specified intents
    intents = Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        channel = client.get_channel(channel_id)
        await channel.send(message)
        await client.close()  # Close the client after sending the message

    # Start the client
    await client.start(DISCORD_TOKEN)

def format_game_data(parsed_data):
    # Create a formatted string representation of the game data
    players_info = "\n".join(
        f"\t**ID**: {player['id']}\n"
        f"\t**Name**: {player['name']}\n"
        f"\t**Role**: {player['role']}\n"
        f"\t**Type**: {player['type']}\n"
        f"\t**Alignment**: {player['alignment']}\n"
        for player in parsed_data['players']
    )
    
    # Format the final message
    message = (
        f"**Game ID**: {parsed_data['game_id']}\n"
        f"**Winner**: {parsed_data['winner']}\n"
        f"**Players**:\n{players_info}\n"
        f"-------------------"  # Add a divider
    )
    return message

if __name__ == '__main__':
    input_file = 'game_data.json'  # Input file with game data
    output_file = 'game_logs.json'   # Output file for game logs
    player_ids_file = 'player_ids.json'  # File for player IDs and names
    characters_file = 'characters.json'  # File for character data

    # Load player IDs and names from player_ids.json
    player_ids = load_player_ids(player_ids_file)

    # Load characters from characters.json
    characters = load_characters(characters_file)

    # Parse the game data
    parsed_game_data = parse_game_data(input_file, player_ids, characters)

    # Allow user to change player alignments if needed
    toggle_alignment(parsed_game_data['players'])

    # Save the parsed data to the output JSON file
    save_to_json(parsed_game_data, output_file)

    print("Game data parsed and saved to 'game_logs.json'.")

    # Format the game data for Discord
    discord_message = format_game_data(parsed_game_data)

    # Send the message to Discord
    asyncio.run(send_discord_message(CHANNEL_ID, discord_message))
