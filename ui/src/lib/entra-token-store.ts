let accessToken: string | null = null;

export function setEntraAccessToken(token: string) {
  accessToken = token;
}

export function clearEntraAccessToken() {
  accessToken = null;
}

export function getEntraAccessToken(): string | null {
  return accessToken;
}

