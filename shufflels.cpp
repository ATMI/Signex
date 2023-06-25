#include <iostream>
#include <fstream>
#include <filesystem>
#include <list>
#include <cstring>

typedef struct {
	std::string filename;
	unsigned random;
} entry_t;

int main(int argc, char **argv) {
	if (argc > 3) {
		const auto &path = argv[1];
		const auto &extension = argv[2];
		auto percent = atoi(argv[3]);
		if (percent > 100 || percent < 0) {
			percent = 80;
		}
		try {
			std::list<entry_t> list;
			srand(time(nullptr));
			for (const auto &entry: std::filesystem::directory_iterator(path)) {
				if (entry.is_regular_file()) {
					auto name = entry.path();
					auto name_str = name.string();
					auto name_ext = name.extension().string();
					auto s = name_ext.c_str();
					if (s[0] == '.' && !strcmp(&s[1], extension)) {
						list.push_back({name.string(), (unsigned) rand() * (unsigned) rand()});
					}
				}
			}
			list.sort([](const entry_t &a, const entry_t &b) { return a.random < b.random; });
			const auto train_count = list.size() * percent / 100;

			std::ofstream f("train.lst", std::ios_base::app);
			auto it = list.cbegin();
			for (size_t i = 0; i < train_count; i++, it++) {
				f << it->filename << std::endl;
			}
			f.close();

			f = std::ofstream("test.lst", std::ios_base::app);
			while (it != list.end()) {
				f << it++->filename << std::endl;
			}
			f.close();
		}
		catch (const std::exception &e) {
			std::cerr << e.what();
		}
	}
	else {
		std::cout << "Usage:\r\n\tshufflels directory extension percent_train";
	}
}

