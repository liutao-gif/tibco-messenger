import com.tibco.tibrv.*;

/**
 * Tibco RV SendRequest helper — called from Python Tibco Messenger.
 *
 * Usage: java TibcoRequest <service> <network> <daemon> <subject> <timeout> <xml>
 *
 * Outputs the reply DATA field value to stdout on success.
 * Exit codes: 0=success, 2=timeout, 3=error
 */
public class TibcoRequest {

    public static void main(String[] args) {
        if (args.length < 6) {
            System.err.println("Usage: TibcoRequest <service> <network> <daemon> <subject> <timeout> <xml>");
            System.exit(1);
        }

        String service = args[0];
        String network = args[1];
        String daemon = args[2];
        String subject = args[3];
        double timeout = Double.parseDouble(args[4]);
        String xmlBody = args[5];

        TibrvRvdTransport transport = null;

        try {
            // 0. Set UTF-8 encoding
            TibrvMsg.setStringEncoding("UTF-8");

            // 1. Open Tibco environment
            Tibrv.open(Tibrv.IMPL_NATIVE);

            // 2. Create transport
            transport = new TibrvRvdTransport(service, network, daemon);

            // 3. Create request message
            TibrvMsg request = new TibrvMsg();
            request.setSendSubject(subject);
            request.add("DATA", xmlBody);

            // 4. Send request and wait for reply (inbox created automatically)
            TibrvMsg reply = transport.sendRequest(request, timeout);

            // 5. Extract reply DATA field
            if (reply != null) {
                Object data = reply.get("DATA");
                if (data != null) {
                    System.out.print(data.toString());
                    transport.destroy();
                    Tibrv.close();
                    System.exit(0);
                }
            }

            // Timeout — no reply
            System.err.println("TIMEOUT: No reply received within " + timeout + " seconds");
            transport.destroy();
            Tibrv.close();
            System.exit(2);

        } catch (TibrvException e) {
            System.err.println("TIBCO_ERROR: " + e.getMessage());
            if (transport != null) {
                try { transport.destroy(); } catch (Exception ignored) {}
            }
            try { Tibrv.close(); } catch (Exception ignored) {}
            System.exit(3);

        } catch (Exception e) {
            System.err.println("ERROR: " + e.getMessage());
            e.printStackTrace(System.err);
            if (transport != null) {
                try { transport.destroy(); } catch (Exception ignored) {}
            }
            try { Tibrv.close(); } catch (Exception ignored) {}
            System.exit(3);
        }
    }
}
