import argparse
from gui import create_app

def main():
    parser = argparse.ArgumentParser(description="1$ Unistroke Recognizer")
    parser.add_argument('-n', '--num_samples', type=int, default=64,
                        help='Number of samples to resample gestures (default: 64)')
    args = parser.parse_args()

    app = create_app(num_samples=args.num_samples)
    app.mainloop()

if __name__ == "__main__":
    main()

# generate requirements.txt: pip freeze > requirements.txt