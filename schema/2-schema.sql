CREATE TABLE estate
(
   id character varying(100) NOT NULL,
   name character varying(500) NOT NULL,
   key_id character varying(100) NOT NULL,
   secret_key character varying(100) NOT NULL,
   CONSTRAINT "PK_ID" PRIMARY KEY (id)
)
WITH (
  OIDS = FALSE
);

GRANT ALL ON TABLE estate TO remembrancer_role;

CREATE TABLE item
(
   hostname character varying(500) NOT NULL,
   due timestamp with time zone NOT NULL,
   estate_id character varying(100) NOT NULL,
   CONSTRAINT "PK_HOSTNAME" PRIMARY KEY (hostname)
)
WITH (
  OIDS = FALSE
);

GRANT ALL ON TABLE item TO remembrancer_role;
