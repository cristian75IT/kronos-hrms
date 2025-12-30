/**
 * KRONOS - Keycloak Configuration
 */
import Keycloak from 'keycloak-js';

const keycloakConfig = {
    url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080/',
    realm: import.meta.env.VITE_KEYCLOAK_REALM || 'kronos',
    clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'kronos-frontend',
};

export const keycloak = new Keycloak(keycloakConfig);

export const keycloakInitOptions = {
    onLoad: 'check-sso' as const,
    checkLoginIframe: false,
    pkceMethod: 'S256' as const,
};

export default keycloak;
