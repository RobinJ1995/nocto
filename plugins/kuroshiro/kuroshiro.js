var path = require ('path');
var Promise = require ('bluebird');
var Kuroshiro = require ('kuroshiro');

var log, api, config;
var handlers = {};

module.exports = (resources) =>
{
	log = resources.log;
	api = resources.api;
	config = resources.config;
	
	return handlers;
};

handlers.enable = (cb) =>
{
	// kuroshiro's own lookup cuts the path at the first "src", which breaks under /usr/src
	var dicPath = path.join (path.dirname (require.resolve ('kuromoji/package.json')), 'dict') + path.sep;
	Kuroshiro.init
	(
		{dicPath: dicPath},
		(error) =>
		{
			if (error)
				return cb (error);
			
			return Promise.resolve ().asCallback (cb);
		}
	);
};

handlers.handleMessage = (message, meta) =>
{
	if (! meta.command || ! meta.fresh)
		return;
	
	var command = meta.command;
	var result;
	switch (command.name.toLowerCase ())
	{
		case 'katakana':
			result = Kuroshiro.toKatakana (command.argument);
			break;
		case 'hiragana':
			result = Kuroshiro.toHiragana (command.argument);
			break;
		case 'romaji':
			result = Kuroshiro.toRomaji (command.argument);
			break;
		case 'kana':
			result = Kuroshiro.toKana (command.argument);
			break;
	}
	
	if (result)
		return msg (message.chat.id, result);
};

function msg (chatId, text)
{
	return api.sendMessage
	(
		{
			chat_id: chatId,
			text: text
		},
		(error, result) =>
		{
			if (error)
				log.trace ('[kuroshiro] Failed to send message', error);
		}
	)
}