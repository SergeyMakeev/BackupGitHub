import argparse
import requests


def get_repos(token: str):

    url = 'https://api.github.com/user/repos'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    res = []
    page_num = 1

    while url:
        print("Page " + str(page_num))
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                # print(repo['full_name'])
                res.append({
                    'full_name': repo['full_name'],
                    'fork': repo['fork'],
                    'stars': repo['stargazers_count'],
                    'clone_url': repo['clone_url'],
                })

            # Check for the 'next' page link
            page_num = page_num + 1
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = None
        else:
            print(f'Failed to retrieve repositories: {response.status_code}')
            break

    return res


def main():

    parser = argparse.ArgumentParser(description='List GitHub repositories.')
    parser.add_argument('token', help='GitHub personal access token')
    args = parser.parse_args()

    token = args.token

    print("Query repos list")
    repos = get_repos(token)

    stars_count = 0
    clone_cmds = []

    print("Name;Fork;Stars;CloneUrl")
    for repo in repos:
        # skip forks
        if repo['fork']:
            continue

        #  skip other organizations' repos
        if not repo['full_name'].startswith('SergeyMakeev'):
            continue

        print(
            repo['full_name'] + ";" +
            str(repo['fork']) + ";" +
            str(repo['stars']) + ";" +
            repo['clone_url']
        )
        clone_cmds.append("git clone --recursive " + repo['clone_url'])
        stars_count = stars_count + repo['stars']

    print("Stars total: " + str(stars_count))
    for cmd in clone_cmds:
        print(cmd)


main()
