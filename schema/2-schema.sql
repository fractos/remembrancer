CREATE TABLE item
(
   hostname character varying(500) NOT NULL,
   due date NOT NULL,
   estate_id character varying(100) NOT NULL,
   region character varying(100) NOT NULL,
   processing boolean NOT NULL,
   CONSTRAINT "PK_HOSTNAME" PRIMARY KEY (hostname)
)
WITH (
  OIDS = FALSE
);

GRANT ALL ON TABLE item TO remembrancer_role;
