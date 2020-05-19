create table if not exists server_instance (
    id text not null,
    active timestamp not null,
    primary key (id)
);

create table if not exists group_instance (
    id serial not null,
    name text not null,
    created_by text not null,
    primary key (id)
);

create table if not exists user_server (
    user_id text not null,
    server_id text not null,
    primary key (user_id, server_id),
    foreign key (server_id) references server_instance(id)
);

create table if not exists group_server (
    group_id integer not null,
    server_id text not null,
    primary key (group_id, server_id),
    foreign key (group_id) references group_instance(id),
    foreign key (server_id) references server_instance(id)
);

create table if not exists command (
    id bigserial not null,
    body text not null,
    running boolean not null,
    user_id text not null,
    server_id text not null,
    primary key (id),
    foreign key (server_id) references server_instance(id)
);
