USE mycloude;

-- this creates a tmp user for testing
CALL insert_user(
    'admin',
    '$argon2id$v=19$m=65536,t=3,p=4$EqI0pjQGoDTGOCdECIFQKg$sx2r5m1K9e+L0oW/sA26XN5t20T2TRfftFBDKGNqpW8'
);
