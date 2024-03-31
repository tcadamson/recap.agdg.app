create table game (
    game_id integer primary key autoincrement,
    title text not null unique collate nocase,
    dev text,
    tools text,
    web text
);

create table post (
    post_id integer primary key autoincrement,
    game_id integer not null references game (game_id)
        on update cascade
        on delete cascade,
    unix integer not null,
    filename text,
    progress text not null
);
