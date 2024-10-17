--Run All to setup schema to an intial state.

--Times
create table
  public.times (
    id bigint generated by default as identity not null,
    day text not null,
    time bigint not null,
    constraint times_pkey primary key (id),
    constraint times_id_key unique (id)
  ) tablespace pg_default;
--Potion Menu
create table
  public.potion_menu (
    sku text not null,
    name text not null,
    red bigint not null,
    green bigint not null,
    blue bigint not null,
    dark bigint not null,
    current_price bigint null,
    id bigint generated by default as identity not null,
    constraint potion_menu_pkey primary key (id),
    constraint potion_menu_sku_key unique (sku),
    constraint potion_storage_id_key unique (id)
  ) tablespace pg_default; 
--Customer Visit
create table
  public.customer_visit (
    id bigint generated by default as identity not null,
    customer_name text not null,
    character_class text not null,
    character_level bigint not null,
    visit_id bigint not null,
    date_id bigint not null,
    constraint customer_visit_pkey primary key (id),
    constraint customer_visit_id_key unique (id),
    constraint customer_visit_date_id_fkey foreign key (date_id) references times (id)
  ) tablespace pg_default;
--Payment
create table
  public.carts (
    id bigint generated by default as identity not null,
    customer_id bigint not null,
    payment text null,
    constraint carts_pkey primary key (id),
    constraint carts_id_key unique (id),
    constraint carts_customer_id_fkey foreign key (customer_id) references customer_visit (id)
  ) tablespace pg_default;
--Cart Items
create table
  public.cart_items (
    cart_id bigint not null,
    sku text not null,
    quantity bigint not null,
    sales_price bigint not null,
    constraint cart_items_pkey primary key (cart_id, sku),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (id),
    constraint cart_items_sku_fkey foreign key (sku) references potion_menu (sku)
  ) tablespace pg_default;
--catalog log (datatracking only)
create table
  public.catalog_log (
    time_id bigint generated by default as identity not null,
    sku text not null,
    bought bigint null,
    constraint catalog_log_pkey primary key (time_id, sku),
    constraint catalog_log_time_id_key unique (time_id),
    constraint catalog_log_sku_fkey foreign key (sku) references potion_menu (sku),
    constraint catalog_log_time_id_fkey foreign key (time_id) references times (id)
  ) tablespace pg_default;
--Transactions
create table
  public.transactions (
    id bigint generated by default as identity not null,
    transaction_type text not null,
    time_id bigint not null,
    order_id bigint not null,
    constraint transactions_pkey primary key (id),
    constraint transactions_id_key unique (id),
    constraint transactions_time_id_fkey foreign key (time_id) references times (id)
  ) tablespace pg_default;
--Gold Ledegr
create table
  public.gold_ledger (
    transaction_id bigint not null,
    gold_quantity bigint not null,
    constraint gold_ledger_pkey primary key (transaction_id),
    constraint gold_ledger_transaction_id_key unique (transaction_id),
    constraint gold_ledger_transaction_id_fkey foreign key (transaction_id) references transactions (id)
  ) tablespace pg_default;
--ml Ledger
create table
  public.ml_ledger (
    transaction_id bigint not null,
    ml_type bigint not null,
    ml_quantity bigint not null,
    barrel_potion_sku text not null,
    cost bigint not null,
    constraint ml_ledger_pkey primary key (transaction_id, ml_type, barrel_potion_sku),
    constraint ml_ledger_transaction_id_fkey foreign key (transaction_id) references transactions (id)
  ) tablespace pg_default;
--Potion Ledger
create table
  public.potion_ledger (
    transaction_id bigint not null,
    sku text not null,
    potion_quantity bigint not null,
    sales_price bigint not null,
    constraint potion_ledger_pkey primary key (transaction_id, sku),
    constraint potion_ledger_sku_fkey foreign key (sku) references potion_menu (sku),
    constraint potion_ledger_transaction_id_fkey foreign key (transaction_id) references transactions (id)
  ) tablespace pg_default;
--Upgrade Ledger
create table
  public.upgrade_ledger (
    transaction_id bigint not null,
    potion_upgrades bigint not null,
    ml_upgrades bigint not null,
    constraint upgrade_ledger_pkey primary key (transaction_id),
    constraint upgrade_ledger_transaction_id_key unique (transaction_id),
    constraint upgrade_ledger_transaction_id_fkey foreign key (transaction_id) references transactions (id)
  ) tablespace pg_default;

--Setup Ledgers and intial TIme
INSERT INTO times (day, time) VALUES ( 'SETUP_DAY', 0);
INSERT INTO transactions (transaction_type, time_id, order_id) SELECT 'SETUP', max(times.id), 0 FROM times;
INSERT INTO upgrade_ledger (transaction_id, potion_upgrades, ml_upgrades) SELECT max(transactions.id), 1, 1 FROM transactions;
INSERT INTO ml_ledger (transaction_id, barrel_potion_sku, ml_type, ml_quantity, cost) SELECT max(transactions.id), 'SETUP_RED', 0, 0, 0 FROM transactions;
INSERT INTO ml_ledger (transaction_id, barrel_potion_sku, ml_type, ml_quantity, cost) SELECT max(transactions.id), 'SETUP_GREEN', 1, 0, 0 FROM transactions;
INSERT INTO ml_ledger (transaction_id, barrel_potion_sku, ml_type, ml_quantity, cost) SELECT max(transactions.id), 'SETUP_BLUE', 2, 0, 0 FROM transactions;
INSERT INTO ml_ledger (transaction_id, barrel_potion_sku, ml_type, ml_quantity, cost) SELECT max(transactions.id), 'SETUP_DARK', 3, 0, 0 FROM transactions;
INSERT INTO gold_ledger (transaction_id, gold_quantity) SELECT max(transactions.id), 100 FROM transactions;
INSERT INTO potion_menu (sku, name, red, green, blue, dark, current_price) VALUES 
    ('0R_0G_0B_100D', 'Mystery potion', 0, 0, 0, 100, 0), 
    ('0R_0G_50B_50D', 'Mystery potion', 0, 0, 50, 50, 0), 
    ('0R_0G_100B_0D', 'Mystery potion', 0, 0, 100, 0, 0), 
    ('0R_50G_0B_50D', 'Mystery potion', 0, 50, 0, 50, 0), 
    ('0R_50G_50B_0D', 'Mystery potion', 0, 50, 50, 0, 0), 
    ('0R_100G_0B_0D', 'Mystery potion', 0, 100, 0, 0, 0), 
    ('50R_0G_0B_50D', 'Mystery potion', 50, 0, 0, 50, 0), 
    ('50R_0G_50B_0D', 'Mystery potion', 50, 0, 50, 0, 0), 
    ('50R_50G_0B_0D', 'Mystery potion', 50, 50, 0, 0, 0), 
    ('100R_0G_0B_0D', 'Mystery potion', 100, 0, 0, 0, 0);