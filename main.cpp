#include <iostream>
#include <darknet.h>
#include <filesystem>

#include "Args.h"

int main(int argc, char *argv[]) {
	try {
		Args args(argc, argv);

		const auto &image_file_iter = args.find("image");
		if (image_file_iter == args.cend()) {
			std::printf("Please, specify image file to process\n");
			return 1;
		}

		const std::string &image_file = image_file_iter->second;
		image im = load_image_color(image_file.c_str(), 0, 0);

		std::string weights_file = args.get("weights", "../models/net.backup");
		std::string labels_file = args.get("labels", "../cfg/classes.lst");
		std::string net_file = args.get("net", "../cfg/net.cfg");

		int classes_count = args.get("classes", 2);
		float thresh = args.get("thresh", 0.5f);
		float hier = args.get("hier", 0.5f);

		network *net = load_network(net_file.c_str(), weights_file.c_str(), 0);
		network_predict_image(net, im);
		detection *det = get_network_boxes(net, im.w, im.h, thresh, hier, nullptr, 1, &classes_count);

		image **alphabet = load_alphabet();
		char **labels = get_labels(labels_file.c_str());
		draw_detections(im, det, classes_count, thresh, labels, alphabet, classes_count);
		save_image(im, "detections");
	} catch (std::exception &e) {
		std::printf("%s\n", e.what());
		return 1;
	}

	return 0;
}
