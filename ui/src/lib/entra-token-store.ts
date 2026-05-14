let accessToken: string | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setEntraAccessToken(token: string) {
  if (accessToken === token) {
    return;
  }
  accessToken = token;
  emit();
}

export function clearEntraAccessToken() {
  if (!accessToken) {
    return;
  }
  accessToken = null;
  emit();
}

export function getEntraAccessToken(): string | null {
  return accessToken;
}

export function subscribeToEntraAccessToken(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
