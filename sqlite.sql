INSERT INTO document_types (description, afip_code)
VALUES ('Factura A', '001');

INSERT INTO documents (id, issuance, settlement, accounting_entry_id, type_id)
VALUES (258998275037863254495938154843991418905, '2023-02-28','2023-03-1',null,'001');


INSERT INTO accounting_entries (id, name, date_created, date_updated)
VALUES (303383700635017643173391516788807239943, 'test', '2021-02-28', '2021-02-28');

UPDATE documents SET accounting_entry_id = 303383700635017643173391516788807239943 WHERE id = 258998275037863254495938154843991418905;
