-- Schema for recap database

-- Games data; information about each project
create table games (
    id integer primary key autoincrement,
    title text collate NOCASE not null unique,
    dev text not null,
    tools text not null,
    web text not null
);

-- Posts data; information about each progress post
-- If no media is attached, the unix timestamp will be lower resolution (no image upload microtime), and the extension will be empty
create table posts (
    id integer primary key autoincrement,
    game_id integer not null references games (id)
        on update cascade
        on delete cascade,
    unix integer not null unique,
    ext text not null,
    progress text not null
);
