let accessToken: string | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) {
    listener();
  }
}

export function setClerkAccessToken(token: string) {
  if (accessToken === token) {
    return;
  }
  accessToken = token;
  emit();
}

export function clearClerkAccessToken() {
  if (!accessToken) {
    return;
  }
  accessToken = null;
  emit();
}

export function getClerkAccessToken(): string | null {
  return accessToken;
}

export function subscribeToClerkAccessToken(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
