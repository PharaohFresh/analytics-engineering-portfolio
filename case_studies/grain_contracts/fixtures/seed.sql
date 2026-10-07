CREATE TABLE orders (order_id TEXT);
CREATE TABLE physical_items (item_id TEXT, order_id TEXT, product_id TEXT, sale_cents INTEGER);
CREATE TABLE products (product_id TEXT, category TEXT);
CREATE TABLE customizations (customization_id TEXT, item_id TEXT, kind TEXT);
INSERT INTO orders VALUES ('order-one'), ('order-two'), ('order-three');
INSERT INTO products VALUES ('mug', 'Drinkware'), ('bag', 'Bags'), ('cap', 'Headwear');
INSERT INTO physical_items VALUES
 ('item-one', 'order-one', 'mug', 10000),
 ('item-two', 'order-one', 'bag', 15000),
 ('item-three', 'order-two', 'mug', 8000),
 ('item-four', 'order-two', 'unmapped-product', 12000),
 ('item-five', 'order-three', 'cap', 5000);
INSERT INTO customizations VALUES
 ('design-one', 'item-one', 'engraving'), ('design-two', 'item-one', 'color'),
 ('design-three', 'item-one', 'placement'), ('design-four', 'item-two', 'patch'),
 ('design-five', 'item-two', 'initials'), ('design-six', 'item-four', 'wrap'),
 ('design-seven', 'item-five', 'embroidery');
