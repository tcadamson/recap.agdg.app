create table game (
    id integer primary key autoincrement,
    title text not null unique collate nocase,
    dev text,
    tools text,
    web text
);

create table post (
    id integer primary key autoincrement,
    game_id integer not null references game (id)
        on update cascade
        on delete cascade,
    unix integer not null,
    filename text,
    progress text not null
);
