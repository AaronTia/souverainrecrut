/**
 * Variables d'environnement pour les tests.
 *
 * Valeurs fictives uniquement : aucun vrai secret ici.
 * "??=" permet à Jenkins de les surcharger si besoin.
 */
process.env.NODE_ENV ??= "test";
process.env.JWT_SECRET ??= "test-jwt-secret-not-for-production";
process.env.API_VERSION ??= "v1";
