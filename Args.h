//
// Created by a on 6/26/23.
//

#ifndef ARGS_H
#define ARGS_H


#include <unordered_map>
#include <functional>

#define PREFIX "--"
#define PREFIX_SIZE (sizeof(PREFIX) - 1)
#define INVALID_ARGUMENT_FORMAT "Argument '%s' has invalid format"

class Args {
protected:
	std::unordered_map<std::string, std::string> map;

public:

	Args(int argc, char *argv[]) {
		for (int i = 1; (i + 1) < argc; i += 2) {
			char *name = argv[i];

			if (strncmp(name, PREFIX, PREFIX_SIZE) != 0) {
				int size = std::snprintf(nullptr, 0, INVALID_ARGUMENT_FORMAT, name) + 1;
				char error[size];
				std::snprintf(error, size, INVALID_ARGUMENT_FORMAT, name);
				throw std::invalid_argument(error);
			}

			char *value = argv[i + 1];
			map[std::string(&name[PREFIX_SIZE])] = std::string(value);
		}
	}

	std::unordered_map<std::string, std::string>::const_iterator find(const std::string &name) const {
		return map.find(name);
	}

	const std::string &get(const std::string &name) const {
		return map.at(name);
	}

	const std::string &get(const std::string &name, const std::string &def) const {
		auto iter = map.find(name);
		if (iter != map.cend()) {
			return iter->second;
		}
		return def;
	}

	template<typename T>
	T get(const std::string &name, const std::function<T(const std::string &)> &conv) const {
		return conv(get(name));
	}

	template<typename T>
	T get(const std::string &name, const T &def, const std::function<T(const std::string &)> &conv) const {
		auto iter = map.find(name);
		if (iter != map.cend()) {
			return conv(iter->second);
		}
		return def;
	}

	std::unordered_map<std::string, std::string>::const_iterator cend() const {
		return map.cend();
	}

	float get(const std::string &name, float def) {
		return get<float>(name, def, [](const std::string &str) { return std::stof(str); });
	}

	int get(const std::string &name, int def) {
		return get<int>(name, def, [](const std::string &str) { return std::stoi(str); });
	}
};


#endif // ARGS_H
