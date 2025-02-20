from ops_agent import OpsAgent

def main():
    agent = OpsAgent(
        wiki_domain="https://wiki.eniot.io/",
        wiki_username="yue.zhang5",
        wiki_password="Hello.135",
        persist_directory="/Users/zhangyue/Documents/code/AI"  # Specify the local Chroma database path
    )

    # Ask if initialization is needed
    initialize = input("Do you want to initialize the vector database? (yes/no): ").strip().lower()
    if initialize == 'yes':
        page_id = input("Enter the page ID to initialize from: ").strip()
        agent.initialize(page_id)
    else:
        print("Skipping vector database initialization.")

    # Start interactive Q&A
    print("\nInteractive Q&A started. Type 'exit' to quit.")
    while True:
        question = input("\nYour question: ").strip()
        if question.lower() == 'exit':
            break
        response = agent.query(question)
        print(f"\nAnswer: {response}")

if __name__ == "__main__":
    main() 