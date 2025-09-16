import json
import sys

def main():
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    name = params.get('name', 'World')
    print(f"Hello, {name} from Python!")

if __name__ == '__main__':
    main()
