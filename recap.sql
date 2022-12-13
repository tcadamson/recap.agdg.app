-- Schema for recap database

-- Games data; information about each game
create table games (
    game_id integer primary key autoincrement,
    game text unique not null,
    dev text not null,
    tools text not null,
    web text not null
);

-- Posts data; information about each recap post
-- If media is attached, the unix timestamp will be higher resolution (due to image upload microtime), and ext will be nonempty
create table posts (
    post_id integer primary key autoincrement,
    game_id integer not null,
    unix integer not null,
    ext text not null,
    progress text not null,
    foreign key (game_id) references games (game_id)
        on update cascade
        on delete cascade
);
