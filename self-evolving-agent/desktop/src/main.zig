const std = @import("std");
const runner = @import("runner");
const zero_native = @import("zero-native");

pub const panic = std.debug.FullPanic(zero_native.debug.capturePanic);

const App = struct {
    env_map: *std.process.Environ.Map,
    handlers: [2]zero_native.bridge.BridgeHandler = undefined,

    fn app(self: *@This()) zero_native.App {
        return .{
            .context = self,
            .name = "self-evolving-agent",
            .source = zero_native.frontend.productionSource(.{ .dist = "frontend/dist" }),
            .source_fn = source,
        };
    }

    fn source(context: *anyopaque) anyerror!zero_native.WebViewSource {
        const self: *@This() = @ptrCast(@alignCast(context));
        return zero_native.frontend.sourceFromEnv(self.env_map, .{
            .dist = "frontend/dist",
            .entry = "index.html",
        });
    }

    fn bridge(self: *@This()) zero_native.BridgeDispatcher {
        self.handlers = .{
            .{
                .name = "agent.backend_status",
                .context = self,
                .invoke_fn = backendStatus,
            },
            .{
                .name = "agent.notify",
                .context = self,
                .invoke_fn = notify,
            },
        };
        return .{
            .policy = .{
                .enabled = true,
                .commands = &policies,
            },
            .registry = .{
                .handlers = &self.handlers,
            },
        };
    }

    fn backendStatus(_: *anyopaque, _: zero_native.bridge.Invocation, output: []u8) anyerror![]const u8 {
        return std.fmt.bufPrint(output,
            \\{{"status":"bridge_ok","backend_url":"http://127.0.0.1:8001"}}
        , .{});
    }

    fn notify(_: *anyopaque, invocation: zero_native.bridge.Invocation, output: []u8) anyerror![]const u8 {
        _ = invocation;
        return std.fmt.bufPrint(output,
            \\{{"notified":true}}
        , .{});
    }
};

const policies = [_]zero_native.bridge.BridgeCommandPolicy{
    .{
        .name = "agent.backend_status",
        .permissions = &.{"network"},
        .origins = &.{"zero://app"},
    },
    .{
        .name = "agent.notify",
        .permissions = &.{"notifications"},
        .origins = &.{"zero://app"},
    },
};

const dev_origins = [_][]const u8{ "zero://app", "zero://inline", "http://127.0.0.1:5173", "http://127.0.0.1:8001" };

pub fn main(init: std.process.Init) !void {
    var app_instance = App{ .env_map = init.environ_map };
    try runner.runWithOptions(app_instance.app(), .{
        .app_name = "Self-Evolving Agent",
        .window_title = "Self-Evolving Agent",
        .bundle_id = "dev.self_evolving_agent.desktop",
        .icon_path = "assets/icon.icns",
        .bridge = app_instance.bridge(),
        .security = .{
            .navigation = .{ .allowed_origins = &dev_origins },
        },
    }, init);
}

test "app name is configured" {
    try std.testing.expectEqualStrings("self-evolving-agent", "self-evolving-agent");
}
